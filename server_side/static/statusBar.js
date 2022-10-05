function updateProgressBar(numRated) {
  document.querySelector('.progress-fill').style.width = `${numRated*10}%`;
  document.querySelector('.progress-text').textContent = `${numRated}/10`;
}

$("document").on('submit', '#rate-form', function(e) {
    e.preventDefault();
    $.ajax({
        type: "POST",
        url: "/update-rated",

        complete: function(data) {
            let numRated = data.responseText['num_rated']
            updateProgressBar(numRated)
            console.log(numRated)
        },

    });
});
