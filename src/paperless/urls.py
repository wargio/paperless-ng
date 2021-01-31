from django.conf.urls import include
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import path, re_path
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import RedirectView
from rest_framework.authtoken import views
from rest_framework.routers import DefaultRouter

from django.utils.translation import gettext_lazy as _

from documents.views import (
    CorrespondentViewSet,
    DocumentViewSet,
    LogViewSet,
    TagViewSet,
    DocumentTypeViewSet,
    SearchView,
    IndexView,
    SearchAutoCompleteView,
    StatisticsView,
    PostDocumentView,
    SavedViewViewSet,
    BulkEditView,
    SelectionDataView
)
from paperless.views import FaviconView

api_router = DefaultRouter()
api_router.register(r"correspondents", CorrespondentViewSet)
api_router.register(r"document_types", DocumentTypeViewSet)
api_router.register(r"documents", DocumentViewSet)
api_router.register(r"logs", LogViewSet)
api_router.register(r"tags", TagViewSet)
api_router.register(r"saved_views", SavedViewViewSet)


urlpatterns = [
    re_path(r"^paperless/api/", include([
        re_path(r"^auth/",
                include(('rest_framework.urls', 'rest_framework'),
                        namespace="rest_framework")),

        re_path(r"^search/autocomplete/",
                SearchAutoCompleteView.as_view(),
                name="autocomplete"),

        re_path(r"^search/",
                SearchView.as_view(),
                name="search"),

        re_path(r"^statistics/",
                StatisticsView.as_view(),
                name="statistics"),

        re_path(r"^documents/post_document/", PostDocumentView.as_view(),
                name="post_document"),

        re_path(r"^documents/bulk_edit/", BulkEditView.as_view(),
                name="bulk_edit"),

        re_path(r"^documents/selection_data/", SelectionDataView.as_view(),
                name="selection_data"),

        path('token/', views.obtain_auth_token)

    ] + api_router.urls)),

    re_path(r"^paperless/favicon.ico$", FaviconView.as_view(), name="favicon"),

    re_path(r"paperless/admin/", admin.site.urls),

    re_path(r"^paperless/fetch/", include([
        re_path(
            r"^doc/(?P<pk>\d+)$",
            RedirectView.as_view(url='/paperless/api/documents/%(pk)s/download/'),
        ),
        re_path(
            r"^thumb/(?P<pk>\d+)$",
            RedirectView.as_view(url='/paperless/api/documents/%(pk)s/thumb/'),
        ),
        re_path(
            r"^preview/(?P<pk>\d+)$",
            RedirectView.as_view(url='/paperless/api/documents/%(pk)s/preview/'),
        ),
    ])),

    re_path(r"^paperless/push$", csrf_exempt(
        RedirectView.as_view(url='/paperless/api/documents/post_document/'))),

    # Frontend assets TODO: this is pretty bad, but it works.
    path('paperless/assets/<path:path>',
         RedirectView.as_view(url='/paperless/static/frontend/en-US/assets/%(path)s')),
    # TODO: with localization, this is even worse! :/

    # login, logout
    path('paperless/accounts/', include('django.contrib.auth.urls')),

    # Root of the Frontent
    re_path(r"paperless/.*", login_required(IndexView.as_view())),
]

# Text in each page's <h1> (and above login form).
admin.site.site_header = 'Paperless-ng'
# Text at the end of each page's <title>.
admin.site.site_title = 'Paperless-ng'
# Text at the top of the admin index page.
admin.site.index_title = _('Paperless-ng administration')
