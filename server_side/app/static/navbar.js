const menu = document.querySelector('#burger-toggle');
const navbar = document.querySelector('#navbar')

menu.addEventListener('click', onMenuClick);

function onMenuClick() {
  if (navbar.classList.contains('open')){
    navbar.classList.remove('open');
  } else {
      navbar.classList.add('open');
  }
}
