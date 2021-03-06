import hashlib
import multiprocessing

import logging
import os
import shutil
import uuid

import tqdm
from django import db
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from filelock import FileLock
from whoosh.writing import AsyncWriter

from documents.models import Document
from ... import index
from ...file_handling import create_source_path_directory
from ...mixins import Renderable
from ...parsers import get_parser_class_for_mime_type


logger = logging.getLogger(__name__)


def handle_document(document_id):
    document = Document.objects.get(id=document_id)

    mime_type = document.mime_type

    parser_class = get_parser_class_for_mime_type(mime_type)

    parser = parser_class(logging_group=uuid.uuid4())

    try:
        parser.parse(document.source_path, mime_type)

        if parser.get_archive_path():
            with transaction.atomic():
                with open(parser.get_archive_path(), 'rb') as f:
                    checksum = hashlib.md5(f.read()).hexdigest()
                # i'm going to save first so that in case the file move
                # fails, the database is rolled back.
                # we also don't use save() since that triggers the filehandling
                # logic, and we don't want that yet (file not yet in place)
                Document.objects.filter(pk=document.pk).update(
                    archive_checksum=checksum,
                    content=parser.get_text()
                )
                with FileLock(settings.MEDIA_LOCK):
                    create_source_path_directory(document.archive_path)
                    shutil.move(parser.get_archive_path(),
                                document.archive_path)

        with AsyncWriter(index.open_index()) as writer:
            index.update_document(writer, document)

    except Exception as e:
        logger.error(f"Error while parsing document {document}: {str(e)}")
    finally:
        parser.cleanup()


class Command(Renderable, BaseCommand):

    help = """
        Using the current classification model, assigns correspondents, tags
        and document types to all documents, effectively allowing you to
        back-tag all previously indexed documents with metadata created (or
        modified) after their initial import.
    """.replace("    ", "")

    def __init__(self, *args, **kwargs):
        self.verbosity = 0
        BaseCommand.__init__(self, *args, **kwargs)

    def add_arguments(self, parser):
        parser.add_argument(
            "-f", "--overwrite",
            default=False,
            action="store_true",
            help="Recreates the archived document for documents that already "
                 "have an archived version."
        )
        parser.add_argument(
            "-d", "--document",
            default=None,
            type=int,
            required=False,
            help="Specify the ID of a document, and this command will only "
                 "run on this specific document."
        )

    def handle(self, *args, **options):

        os.makedirs(settings.SCRATCH_DIR, exist_ok=True)

        overwrite = options["overwrite"]

        if options['document']:
            documents = Document.objects.filter(pk=options['document'])
        else:
            documents = Document.objects.all()

        document_ids = list(map(
            lambda doc: doc.id,
            filter(
                lambda d: overwrite or not d.archive_checksum,
                documents
            )
        ))

        # Note to future self: this prevents django from reusing database
        # conncetions between processes, which is bad and does not work
        # with postgres.
        db.connections.close_all()

        try:

            logging.getLogger().handlers[0].level = logging.ERROR
            with multiprocessing.Pool(processes=settings.TASK_WORKERS) as pool:
                list(tqdm.tqdm(
                    pool.imap_unordered(
                        handle_document,
                        document_ids
                    ),
                    total=len(document_ids)
                ))
        except KeyboardInterrupt:
            print("Aborting...")
