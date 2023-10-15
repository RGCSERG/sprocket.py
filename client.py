from sprocket import ClientSocketImpl

client = ClientSocketImpl()

if __name__ == "__main__":
    client.start()
    client.send_websocket_message(
        "wassup using threading now frrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr"
    )
    client.ping()
    print("")  # WHY THE F@'£K DOES THIS f"$£%*G
    client.close()
