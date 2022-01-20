# Comment-Reaction Chat
Simple no-frontend chat with commenting and reacting features.

# How to use
1. In the ```client``` folder execute ```./run.sh``` (or equivalently, ```python3 client.py```)
2. Sing in or sign up (as always).
3. **To send a message,** type 
Any text and press Enter

4. **To write a comment,** type 
```
/c + [message number] + any text 
```
For example, ```/c 42 I'm the bald guy``` will leave the comment "I'm the bald guy" under the message #42. 

5. **To like a message,** type 
```/l + [message number]```

6. **To dislike a message,** type 
```/l + [message number]```

7. **To 🔥 a message,** type 
```/lire + [message number]```

8. **To ❤️️ a message,** type 
```/love + [message number]```

9. **To 💩️ a message,** type 
```/poo + [message number]```

## Command Line User Interface
The *Actions* listed above appear in your terminal. Together with messages you will be receiving realtime notifications about each comment, reaction and sign up.

## File User Interface
You can open ```ui.txt``` to see the chat through a more traditional interface. ```ui.txt``` is a list of messages. Each message is formatted together with comments on the message and reactions sent. 
