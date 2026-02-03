#!/bin/sh

[ "${1}" = '' ] && echo "${0##*/} host.name [pkcs12-password]" && exit 1

for tool in 'mkdir' 'cat' 'openssl'; do
	echo -n "Checking '${tool}'"

	if ! command -v "${tool}" > '/dev/null' 2>&1; then
		echo ' [FAIL]'
		exit 1
	fi

	echo ' [ OK ]'
done

c="EN"
st="None"
l="None"
o="${1}"
cn="${o}"

if [ -e './ssl' ]; then
	echo 'Error: ./ssl already exists'
	exit 1
fi

mkdir './ssl' || exit 1

cat > './ssl/openssl.cnf' << EOF
[ req ]
default_bits       = 2048
distinguished_name = req_distinguished_name
req_extensions     = req_ext
prompt             = no

[ req_distinguished_name ]
C  = ${c}
ST = ${st}
L  = ${l}
O  = ${o}
OU = Server
CN = ${cn}

[ req_ext ]
subjectAltName = @alt_names

[ alt_names ]
DNS.1 = ${cn}
EOF

openssl genrsa -out './ssl/ca.key' 4096
openssl req -x509 -new -nodes -key './ssl/ca.key' -sha256 -days 36500 -out './ssl/ca.pem' -subj "/C=${c}/ST=${st}/L=${l}/O=${o}/OU=CA/CN=${cn}"

openssl genrsa -out './ssl/server.key' 2048
openssl req -new -key './ssl/server.key' -out './ssl/server.csr' -config './ssl/openssl.cnf'
openssl x509 -req -in './ssl/server.csr' -CA './ssl/ca.pem' -CAkey './ssl/ca.key' -CAcreateserial -out './ssl/server.crt' -days 36500 -sha256 -extensions req_ext -extfile './ssl/openssl.cnf'

openssl genrsa -out './ssl/client.key' 2048
openssl req -new -key './ssl/client.key' -out './ssl/client.csr' -subj "/C=${c}/ST=${st}/L=${l}/O=${o}/OU=Client/CN=${cn}"
openssl x509 -req -in './ssl/client.csr' -CA './ssl/ca.pem' -CAkey './ssl/ca.key' -CAcreateserial -out './ssl/client.crt' -days 36500 -sha256

openssl pkcs12 -export -out './ssl/client.p12' -inkey './ssl/client.key' -in './ssl/client.crt' -certfile './ssl/ca.pem' -passout "pass:${2}"
