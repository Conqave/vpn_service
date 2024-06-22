import rsa

def generate_keys():
    # Generowanie kluczy dla serwera
    (server_public_key, server_private_key) = rsa.newkeys(2048)
    with open('server_private_key.pem', 'wb') as f:
        f.write(server_private_key.save_pkcs1('PEM'))
    with open('server_public_key.pem', 'wb') as f:
        f.write(server_public_key.save_pkcs1('PEM'))

    # Generowanie kluczy dla klienta
    (client_public_key, client_private_key) = rsa.newkeys(2048)
    with open('client_private_key.pem', 'wb') as f:
        f.write(client_private_key.save_pkcs1('PEM'))
    with open('client_public_key.pem', 'wb') as f:
        f.write(client_public_key.save_pkcs1('PEM'))

    print("Klucze zostały wygenerowane i zapisane jako pliki PEM.")

if __name__ == "__main__":
    generate_keys()
