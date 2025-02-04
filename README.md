# CLI Temp-Mail

Python command-line script for [temp-mail.io](https://temp-mail.io/).

## Installation

```
python -m pip install git+https://github.com/Oyunsky/cli-temp-mail.git
```

## Usage

To use the script, just run the `tmail` command. The script will create a temporary email and wait for a message to be received.

```
>>> tmail
email: example@email.com
# waiting for recieve message (by default 30 sec)
```

After recieving a message, the script will display it.

```
email: example@email.com
Lorem Ipsum is simply dummy text of the printing and typesetting industry.
Lorem Ipsum has been the industry's standard dummy text ever since the 1500s,
when an unknown printer took a galley of type and scrambled it to make a type specimen book.
It has survived not only five centuries, but also the leap into electronic typesetting,
remaining essentially unchanged. It was popularised in the 1960s with the release of
Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing
software like Aldus PageMaker including versions of Lorem Ipsum.
```
