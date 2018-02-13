SERVER_NAME=example.org
if [ -e cakey.pem ]; then
	echo "Seems like we already have a CA, not generating but using the one in current directory"
else
	echo "Generating CA key"
	openssl genrsa -passout pass:floyd -aes256 -out cakey.pem 2048 >/dev/null
	echo "Generating CA cert"
	openssl req -batch -subj "/CN=Floyds-Simple-CA/" -passin pass:floyd -new -x509 -days 3650 -key cakey.pem -out ca-cert.pem -set_serial 1 >/dev/null
	echo "Generating index and serial"	
	touch index.txt
	echo "01" > serial
	#Diffie-Hellman parameter
	openssl dhparam -out dh1024.pem 1024 >/dev/null
	echo "You need to install ca-cert.pem on your client"
	#Copy to same name file with .cer ending for stupid Android phones, so they are able to install it in the settings
	cp ca-cert.pem ca-cert.crt
	#Example:
	#	The easiest way to transfer the CA to the client is usually executing "python -m SimpleHTTPServer"
	#	in this directory and surf with your client to http://<ip_of_this_host>:8000/
fi
if [ -e serverkey.pem ]; then
	echo "Seems like we already have a server certificate, not generating but using the one in current directory (rm server* to regenerate)"
else
	#Server
	echo "Generating server certificate"
	openssl req -batch -subj "/CN=$SERVER_NAME/" -new -newkey rsa:1024 -nodes -out servercsr.pem -keyout serverkey.pem -days 3650 >/dev/null
	#sign server csr with CA
	echo "Signing server certificate"
	openssl x509 -passin pass:floyd -req -in servercsr.pem -out servercert.pem -CA ca-cert.pem -CAkey cakey.pem -CAserial ./serial -days 3650 >/dev/null
	rm servercsr.pem

	cat ca-cert.pem > chain.pem
	echo "" >> chain.pem
	cat servercert.pem >> chain.pem
fi
