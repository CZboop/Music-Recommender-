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
              const recs = JSON.parse(data.responseText)['recs']
              const pastRecs = JSON.parse(data.responseText)['past_recs']
              if (recs.length == 0){
                let pNode = document.createElement("p");
                pNode.textContent = "Sorry, we couldn't find any new recommendations for you. Rate more artists and try again."
                $(recs_container.appendChild(pNode));
              }
              else {
                for (rec of recs){
                  let pNode = document.createElement("p");
                  pNode.textContent = rec
                  $(recs_container.appendChild(pNode));
                }
              }
              if (0 < recs.length <= 3){
                let pNode = document.createElement("p");
                pNode.textContent = "We're struggling to recommend artists that we haven't recommended before. Rate more artists to get more new recommendations."
                $(recs_container.appendChild(pNode));
              }


              if (pastRecs.length > 0){
                const pastRecHeading = document.createElement("h2");
                pastRecHeading.textContent = "Past Recommendations";
                recs_container.appendChild(pastRecHeading);
                for (let i = pastRecs.length - 1; i >=0; i--){
                  let pNode = document.createElement("p");
                  pNode.textContent = pastRecs[i]
                  $(recs_container.appendChild(pNode));
                }
              }
            }
          });
        }
          })
