  $(function (){
    recs = getRecommendations()

        function getRecommendations(){
          $.ajax({
            url: "/recommend",
            type: "POST",
            dataType: "json",
            beforeSend: function(){
              $('.recs-loading').show();
            },
            complete: function(data){
              $('.recs-loading').hide();
              const recs = JSON.parse(data.responseText)['recs'];
              const pastRecs = JSON.parse(data.responseText)['past_recs'];
              const topSongs = JSON.parse(data.responseText)['top_songs'];
              console.log(topSongs);
              if (Object.keys(recs).length == 0){
                let pNode = document.createElement("p");
                pNode.textContent = "Sorry, we couldn't find any new recommendations for you. Rate more artists and try again."
                $(recs_container.appendChild(pNode));
              }
              else {
                Object.keys(recs).forEach(function(key, index){
                  let pNode = document.createElement("a");
                  pNode.textContent = key
                  pNode.href = recs[key]
                  $(recs_container.appendChild(pNode));
                  lineBreak = document.createElement("br");
                  $(recs_container.appendChild(lineBreak));
                  if (topSongs[index].length > 0){
                    let topSongHeading = document.createElement('h5');
                    topSongHeading.textContent = 'Recommended Songs';
                    $(recs_container.appendChild(topSongHeading));
                    topSongs[index].forEach(function(subArray){
                      console.log(subArray);
                      let topSongsNode = document.createElement("a");
                      topSongsNode.textContent = subArray[0];
                      topSongsNode.href = `https://open.spotify.com/track/${subArray[1]}`;
                      $(recs_container.appendChild(topSongsNode));
                    })
                  }
                })
                if ( Object.keys(recs).length <= 3){
                  let pNode = document.createElement("p");
                  pNode.textContent = "We're struggling to recommend artists that we haven't recommended before. Rate more artists to get more new recommendations."
                  $(recs_container.appendChild(pNode));
                }
              }

              if (Object.keys(pastRecs).length > 0){
                const pastRecHeading = document.createElement("h2");
                pastRecHeading.textContent = "Past Recommendations";
                recs_container.appendChild(pastRecHeading);
                Object.keys(pastRecs).slice().reverse().forEach(function(key){
                  let pNode = document.createElement("a");
                  pNode.textContent = key
                  pNode.href = pastRecs[key]
                  $(recs_container.appendChild(pNode));
                  lineBreak = document.createElement("br");
                  $(recs_container.appendChild(lineBreak));
                })
              }
            }
          });
        }
          })
