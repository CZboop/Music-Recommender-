const letters = document.querySelectorAll(".letter");

setInterval( ()=> {
  for (i of letters){
        let colour = window.getComputedStyle(i).getPropertyValue("color");
    switch(colour){
        case "rgb(255, 0, 0)":
            i.style.color = "orange";
            break;
        case "rgb(255, 165, 0)":
            i.style.color = "yellow";
            break;
        case "rgb(255, 255, 0)":
            i.style.color = "green";
            break;
        case "rgb(0, 128, 0)":
            i.style.color = "blue";
            break;
        case "rgb(0, 0, 255)":
            i.style.color = "indigo";
            break;
        case "rgb(75, 0, 130)":
            i.style.color = "violet";
            break;
        case "rgb(238, 130, 238)":
            i.style.color = "red";
    }
  }
} , 750)
