import { Component, forwardRef, OnInit } from '@angular/core';
import { NG_VALUE_ACCESSOR } from '@angular/forms';
import { AbstractInputComponent } from '../abstract-input';

@Component({
  providers: [{
    provide: NG_VALUE_ACCESSOR,
    useExisting: forwardRef(() => ColorComponent),
    multi: true
  }],
  selector: 'app-input-color',
  templateUrl: './color.component.html',
  styleUrls: ['./color.component.scss']
})
export class ColorComponent extends AbstractInputComponent<string>  {

  constructor() {
    super()
  }

}
