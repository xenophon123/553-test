# Project 6: Streaming Music Service

In this project, you'll be designing and implementing a protocol of your own in order to learn all of the concerns that go into constructing one.
Specifically, you will be building a protocol for a music streaming service in which a server with music files responds to client requests for files.
You'll need to worry about things like header and message formats, proper framing of messages, and the behavior of both sides in response to every message.
In class, we discussed a few approaches to building such a service: simple HTTP gets, a custom streaming protocol like RTSP, or DASH-like chunking via HTTP.
Note that while RTSP is a good strawman, it is likely *much* more complicated than you need for this project.

Since you will be developing the protocol, client, and server, there is no single correct design or architecture.
You just need to be sure that we can run your implementation and play music.


### Requirements

* You will turn in an RFC for your protocol that specifies the exact behavior of your protocol.  You will turn this in before the final implementation so we know that you've thought about your implementation deeply.  The RFC should be like any other RFC - detailed enough that any of the instruction staff could implement their own version just from the description.

* Your implementation should be directly on top of raw sockets.  You should not, for instance, use an HTTP protocol or implementation.

* We have provided skeleton code for a threaded client and server in Python.  Feel free to start from scratch in a different language or with a different architecture (e.g.,  select() statements).  If you choose a different language, you will be responsible for finding libraries that can play mp3 files.

* Your server should be able to handle multiple clients simultaneously.  They should be able join and leave at any time, and the server should continue to operate seamlessly.

* Your client should be interactive and it should know how to handle at least the following commands:
    * `list`: Retrieve a list of songs that are available on the server, along with their ID numbers.
    * `play [song number]`: Begin playing the song with the specified ID number. If another song is already playing, the client should switch immediately to the new one.
    * `stop`: Stops playing the current song, if there is one playing.

* The client should be able to stream, i.e., start playing music before the mp3 has been downloaded and terminate transmission early if the client stops playing the song.  Note that mp3s are designed exactly for this purpose!  If you start feeding  mp3 data frames to a music player, it will be able to play without needing the entire file.

* Similar to the above, the server should be able to handle new commands without needing to finish sending the previous file.  For instance, if it receives a `list` command during playback of a giant music file, the client should be able to see the list of songs immediately.

* The client should not cache data. In other words, if the user tells the client to get a song list or play a song, the two should exchange messages to facilitate this. Don't retrieve an item from the server once and then repeat it back again on subsequent requests.

* One of the parameters to your server should be a path to a directory that contains audio files. Within this directory, you may assume that any file ending in ".mp3" is an mp3 audio file. We have provided three CC-licensed songs as a start.  Feel free to use those or your own mp3 files for testing. **Please do not submit audio files to Canvas!**

* Although your protocol should still work if the connection is slow, it's okay if the song stutters under bad network conditions.  You don't need to handle pre-buffering or adaptive rate streaming.


## Part A: Protocol Design

For the first part of this assignment, you and your partner will be designing your own protocol and describing it in RFC format.
RFCs, or a Requests for Comments, are the documents that we use to communicate methods, protocols, and observations about the Internet.
In the context of standards, RFCs from "IETF Working Groups" ensure that anyone building a network device, operating system, or just looking at packets will be able to understand the protocol and implement it correctly on their own.
Not all RFCs describe Internet standards, however, some of them are just informational.
You've already seen some examples of RFCs in previous projects (esp. HW2) so you should have at least some idea of what they look like.

### Getting started

We've provided a utility that can compile markdown, the markup language used in things like github/bitbucket's README files to RFC format.
If you've never used markdown, don't worry -- it's very easy to use and is an essential tool for today's repo management.
The first step is getting the RFC compilation utility working and compiling some example RFCs.
From your `553-hw6/` directory, run:

```
setup/rfc.sh
cd mmark/rfc
make txt
make html
```

This will generate both the text and the html versions of several actual RFCs.
You should take a look at the `.md` files to see the syntax of Markdown, specifically how the number of #'s changes the size of the section heading and how packet formats are laid out.
RFC7511 includes many features that you might find useful in your descriptions.

### Writing the RFC

The protocol described in the RFC does **not** need to be the protocol you end up implementing (although good design at this stage will help you when you are implementing).
It's okay if, during the course of your implementation, you find and fix bugs in your original protocol implementation.
Thus, we won't be grading on correctness.
Instead, your grade for the RFC will be on clarity, style, and the precision of the wording.
For instance, you should use [RFC2119](https://www.ietf.org/rfc/rfc2119.txt) correctly in your RFCs.

To get you started, here are a few questions that you should ask yourselves during the course of designing the protocol:

* What types of messages does your jukebox protocol send, and what do they mean?
* How are your messages formatted?  Are they text or binary, and what does the header look like?
* How do you determine where one message ends and another begins (i.e., framing)?
* What type of state does the server need to store per-client?  What does that state mean (e.g., the fields in the client struct)?
* How do messages transition the client/server from one state to another?
* Anything else I should know about the way it works?


There is no hard minimum or maximum length as long as you describe the protocol well.
Specifically, you don't need to write thousands of words of text to get full credit as long as you are careful about the text that you do write.
As reference, you should base your RFC on the `.md` files included in the `mmark/rfc/` directory, and look at other RFCs for inspiration.
A few other resources that might be helpful:

[Markdown cheatsheet](https://github.com/adam-p/markdown-here/wiki/Markdown-Cheatsheet)

[mmark markdown information](https://mmark.miek.nl/post/syntax/)

[RFC style guide](https://www.rfc-editor.org/rfc/rfc7322.html)

## Client and server implementation

Your client and server should implement the protocol above (or a fixed version of it).
The implementation should satisfy the requirements at the beginning of this document.
Note that the implementation here is in Python, but the socket interface should be pretty similar to C++.
For example, the Python server should probably do something like:

```
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('', server_port))
s.listen(QUEUE_LENGTH)
```

You can refer to Python's socket API for more information:

[Python socket](https://docs.python.org/2/library/socket.html)

### Getting started

The provided repository contains a few pieces of code:

 * `setup/` contains a few bash scripts for setting up your environment.  We will discuss this below.
 * `client.py` and `server.py` include some skeleton code that you may find helpful for structuring your implementations.
 * `mp3-example.py` is a utility file that just plays mp3 files.  You can use this to test your machine setup and to see how to play an mp3 file from Python.
 * `music` contains the example mp3 files.


The first step is to ensure that you can play music in your Vagrant VM.  Try running from the 553-hw6 directory:

```
python mp3-example.py music/cinematrik\ -\ Revolve.mp3
```

##### Troubleshooting

1. Make sure that the sound on your Host OS is turned all the way up.

2. Depending on your Linux kernel version, you may need to run the following script to patch a compatibility issue with our Vagrantfile and recent Linux kernels:

```
setup/fix.sh
```

3. You may also need to run the following commands after a `vagrant halt` and `vagrant up`.

```
sudo alsa force-reload
sudo alsactl init
amixer set Master 100%
amixer set Master unmute
```

4.  If the `mp3-example.py` script still does not work after the above steps, please post the output of `sudo alsa force-reload` and `sudo alsactl init` to Piazza.


### Helpful hints

* My reference solution requires ~300 lines of code.  Note that less code is typically correlated with better results as it indicates a simpler and more well-thought-out protocol.

* When using threads, be very careful with thread safety.  Python has a threading module that gives you threads, locks, and condition variables.  Note that socket `send`s/`recv`s are thread safe, meaning you can have a thread send() and another thread recv() concurrently without the help of locks, etc.  You probably don't want to execute *split* sends (or recvs) for the same connection in two different threads as messages can become interleaved.

* The python struct module is very useful for serializing and deserializing arbitrary datatypes.

* It's possible that a client closes a connection just before your server attempts to send to it. In this case, by default, two things will happen: 1) your process will receive the SIGPIPE signal, which by default, kills your process, and 2) send will return an error and set errno to EPIPE to indicate the connection (pipe) was broken. Obviously you don't want (1) to occur, since you still want to service other clients. Luckily, we can easily prevent that signal by using the that extra "flags" parameter to send that we've been ignoring thus far. By setting the flags to MSG_NOSIGNAL, the kernel will only do (2), which is a much more convenient way for you to detect and handle a client disconnection.

* You should think a lot about different interleavings of messages as this is an asynchronous system.  For example, what if, between the sending of two chunks of music, the server receives a play-stop-play sequence of messages?  Presumably the result should be that the second play command happens and the first does not.

* Test your code in small increments. It's much easier to localize a bug when you've only changed a few lines.

* If you want your client to begin playing a new file, you need to create a new MadFile object. This tells mad (our audio library) to interpret the next bytes as the beginning of a new file (which includes some metadata) rather than the middle of the previously playing file.


### Submission and grading

For Part A, *one partner* should submit the .txt and .html files generated by `mmark` to Canvas.  Again, see `mmark/rfc/Makefile` for how to do this from a `.md` file.

For Part B, *one partner* should submit the client and server implementations to Canvas.  You should also submit a readme with instructions on how to run your code.  If we can't get it to run, you will lose points!

Adapted with permission from Kevin Webb at Swarthmore College
