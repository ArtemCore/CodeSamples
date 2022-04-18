
const urlForLogin = "%s";
const urlForRegistration = "%s";

const makeRequest = ({urlPath, qr_type, elementId}) => {
    let url = new URL(urlPath);
    params = {'qr_type': qr_type}
    Object.keys(params).forEach(key => url.searchParams.append(key, params[key]))

    fetch(url)
        .then(function(response){
            response.json()
                .then(
                    function(data) {
                        emitQRToken({
                            ...data,
                            qr_type
                        })
                        generateQr(JSON.stringify(data), elementId)
                    })
        })
}


const updateQrLoginFunc = () => makeRequest({
    elementId: 'qrLogin',
    urlPath: urlForLogin,
    qr_type: 'authentication'
});

const updateQrRegistrationFunc = () => makeRequest({
    elementId: 'qrRegistration',
    urlPath: urlForRegistration,
    qr_type: 'registration'
});

document.getElementById("qrLoginExpired").onclick = updateQrLoginFunc;
document.getElementById("updateSignInQR").onclick = updateQrLoginFunc;

document.getElementById("qrRegistrationExpired").onclick = updateQrRegistrationFunc;
document.getElementById("updateSignUpQR").onclick = updateQrRegistrationFunc;

emitQRToken(%s)
emitQRToken(%s)

generateQr("%s", "qrLogin")
generateQr("%s", "qrRegistration")
