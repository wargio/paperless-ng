import { animate, state, style, transition, trigger } from "@angular/animations";

export const fadeAnimation = [

  trigger("fade", [
    state("visible", style({
      opacity: 1
    })),
    state("invisible", style({
      opacity: 0.0
    })),
    transition("visible => invisible", animate(0)),
    transition("invisible => visible", animate(100))
  ])
  
]