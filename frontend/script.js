document.addEventListener('DOMContentLoaded', function() {

        const messagesContainer = document.getElementById('messages-container');
        const offset = 0;
        const limit = 5;
        const example_message_footer = document.getElementById("example-message-footer").innerHTML;
        const BACKEND_URL = 'https://api.rtts.site';
        
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
                    
                    messages.reverse().forEach(message => {
                        addMessageToUI(message);
                    });
                    
                } catch (err) {
                    console.error('Ошибка загрузки сообщений:', err);
                }
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
                            messageContent.appendChild(video);
                            break;

                }
                const text = document.createElement('p');
                            text.textContent  = message.message;
                            messageContent.appendChild(text);
                

                            
                const messageFooter = document.createElement('div');
                messageFooter.className = 'message-footer'
                messageFooter.innerHTML = example_message_footer

                console.log(messageFooter.innerHTML)
                
                messageContent.appendChild(messageFooter)
                messageElement.appendChild(messageContent)
                
                
                // Вставляем новое сообщение в начало
                messagesContainer.insertBefore(messageElement, messagesContainer.firstChild);
                

        }
        connectToBackend();

      } );