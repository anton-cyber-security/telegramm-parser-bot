document.addEventListener('DOMContentLoaded', function() {

        const messagesContainer = document.getElementById('messages-container');
        let offset = 0;
        let limit = 5;
        const message_ids = new Array();
        const BACKEND_URL = messagesContainer.dataset.backend;
        
        function checkScrollRight(element) {
            // Проверяем, достигнут ли правый конец
            const isAtRightEnd = element.scrollWidth - element.scrollLeft === element.clientWidth;
            
            // Допуск в 1-2 пикселя для избежания неточностей
            const isAtRightEndWithTolerance = Math.abs(
                element.scrollWidth - element.scrollLeft - element.clientWidth
            ) <= 2;
            
            return isAtRightEndWithTolerance;
        }

        // Использование
        const scrollableElement = document.getElementById('CardsMessageContainer');

        scrollableElement.addEventListener('scroll', function() {
            if (checkScrollRight(this)) {
                loadMessages()
            }
        });
        function connectToBackend() {
     
            // Очищаем контейнер сообщений
            messagesContainer.innerHTML = '';
            
            // Загружаем историю сообщений
            loadMessages();
            
        }

        async function loadMessages() {
                try {
                    const response = await fetch(`${BACKEND_URL}/messages?limit=${limit}&offset=${offset}`);
                    const response_json = await response.json();
                    const messages = response_json.all_group_messages
                    
                    console.log(messages)
                    
                    messages.reverse().forEach(message => {
                        if (message_ids.includes(message.message_id)){
                        }
                        else {
                          message_ids.push(message.message_id)
                          addMessageToUI(message);
                        }
                        
                    });
                    offset = offset + 5
                    console.log(offset)


                    

                } catch (err) {
                    console.error('Ошибка загрузки сообщений:', err);
                }
        }

        function getFirstWords(text, wordCount = 30, addEllipsis = true) {
              if (!text || typeof text !== 'string') return '';
              
              const words = text.trim().split(/\s+/);
              
              if (words.length <= wordCount) {
                  return text;
              }
              
              const result = words.slice(0, wordCount).join(' ');
              return addEllipsis ? result + '...' : result;
          }

        function addMessageToUI(message) {
                const messageElement = document.createElement('div');
                messageElement.className = 'message';
                
                const messageContent = document.createElement('div');
                messageContent.className = 'message-content'
                
                switch(message.type_media) {
                        case 'photo':
                            const img = document.createElement('img');
                            img.src = message.media;
                            img.alt = 'Egida Telecom';
                            messageContent.appendChild(img);
                            break;
                        
                        case 'video':
                            const video = document.createElement('video');
                            video.src = message.media;
                            video.controls = false;
                            video.setAttribute("autoplay", "autoplay");
                            video.setAttribute("muted", "muted"); 
                            video.setAttribute("playsinline", "playsinline");
                            video.setAttribute("loop", "loop");
                            messageContent.appendChild(video);
                            break;
                        
                        case 'unknown':
                            const img_base = document.createElement('img');
                            img_base.src = "https://optim.tildacdn.com/tild3333-3739-4830-b230-343237313965/-/resize/340x/-/format/webp/photo.png.webp";
                            img_base.alt = 'Egida Telecom';
                            messageContent.appendChild(img_base);
                            break;
                            
                        

                }
                const text = document.createElement('p');
                            text.textContent  = getFirstWords(message.message, 20, true);
                            messageContent.appendChild(text);
                
                

                            
                const messageFooter = document.createElement('div');
                messageFooter.className = 'message-footer'


                const messageFooter_element_a_1= document.createElement('a');
                messageFooter_element_a_1.className = "icon-button-news"
                messageFooter_element_a_1.href = message.link_to_message_in_telegram	

                const messageFooter_element_svg =  document.createElementNS('http://www.w3.org/2000/svg' , 'svg');
                messageFooter_element_svg.setAttribute('class' ,"icon");
                messageFooter_element_svg.setAttribute('viewBox', '0 0 24 24');

                const messageFooter_element_path = document.createElementNS('http://www.w3.org/2000/svg', 'path');

                messageFooter_element_path.setAttribute('d', "M7 17L17 7M17 7H7M17 7V17")
                messageFooter_element_path.setAttribute('stroke', "black")
                messageFooter_element_path.setAttribute('fill', "none")
                messageFooter_element_path.setAttribute('stroke-linejoin', "round")
                messageFooter_element_path.setAttribute('stroke-linecap', "round")
                messageFooter_element_path.setAttribute('stroke-width', "2")
                
                const messageFooter_element_a_2= document.createElement('a');
                messageFooter_element_a_2.className = "more-text"
                messageFooter_element_a_2.href = message.link_to_message_in_telegram
                messageFooter_element_a_2.textContent = "ЧИТАТЬ ПОЛНОСТЬЮ"

                
                
                messageFooter_element_svg.appendChild(messageFooter_element_path)
                messageFooter_element_a_1.appendChild(messageFooter_element_svg)

                messageFooter.appendChild(messageFooter_element_a_1)
                messageFooter.appendChild(messageFooter_element_a_2)
                
                messageContent.appendChild(messageFooter)
                messageElement.appendChild(messageContent)
                
                
                // Вставляем новое сообщение в начало
                messagesContainer.appendChild(messageElement);
                

        }

        
        connectToBackend();

      } );