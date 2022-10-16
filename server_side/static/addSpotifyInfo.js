$(function (){
    addSpotifyInfo();
    
        function addSpotifyInfo(){
          $.ajax({
            url: "/add-spotify-info",
            type: "POST",
            dataType: "json",
            beforeSend: function(){
              
            },
            complete: function(data){
                $('.import-loading').hide();
                $('.logged-in').show();
        }
          })
        }
    }
)
