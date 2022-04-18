if ('%(standalone)s' !== 'True') {

    let currentTimerIdAndTypeOfRequest = {};

    function emitQRToken(data) {
        const {qr_type} = data;
        const qrLoginExpired = document.getElementById('qrLoginExpired');
        const qrRegistrationExpired = document.getElementById('qrRegistrationExpired');

        let timeRange = 45; //period when the request will be sent (in sec)
        let startTime;

        const qrVisibilityFunc = (hide) => {
            switch (qr_type) {
                case 'authentication':
                    timeRange = 45;
                    qrLoginExpired.style.visibility = hide ? 'hidden' : 'visible';
                    break;
                case 'registration':
                    timeRange = 120;
                    qrRegistrationExpired.style.visibility = hide ? 'hidden' : 'visible';
                    break;
                default:
                    break;
            }
            startTime = Date.now() + timeRange * 1000;
        }

        const getQrToken = async () => {
            try {
                const response = await fetch('%(ajax_login_url)s', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
                    body: JSON.stringify(data)
                });
                if (response.status === 200) {
                    const serviceCookie = await response.json(); // extract JSON from the http response
                    SetServiceCookie(serviceCookie)
                }
            } catch (err) {
                console.log(err);
            } finally {
                const finishTime = Date.now();

                if (finishTime < startTime) {
                    const timeout = qr_type == 'authentication' ? 2000 : 3000;
                    currentTimerIdAndTypeOfRequest[qr_type] = setTimeout(getQrToken, timeout);
                } else {
                    qrVisibilityFunc(false)
                }
            }
        }

        qrVisibilityFunc(true)
        clearTimeout(currentTimerIdAndTypeOfRequest[qr_type]);
        getQrToken();
    }



    if (('%(is_auth_service)s' !== 'True') && ('%(sso_mode)s' === 'True')){
        const sso_login = document.getElementById("ssoSignIn");
        sso_login.onclick = make_sso_login
    }
    checkCookie();
}

//Sign in form behavior
const signInEmailInput = document.getElementById('inputEmailSignIn')
const signInPasswordInput = document.getElementById('inputPassword')
const signInBtn = document.getElementById('btnSignInForm')

const checkSignInInputs = () => signInBtn.disabled = signInEmailInput.value.length === 0 || signInPasswordInput.value.length === 0;

signInEmailInput.oninput = () => checkSignInInputs();
signInPasswordInput.oninput = () => checkSignInInputs();

checkSignInInputs();

//Sign up form behavior
const firstNameSignUpInput = document.getElementById('inputFirstName')
const lastNameSignUpInput = document.getElementById('inputSurname')
const emailSignUpInput = document.getElementById('inputEmailSignUp')
const passwordSignUpInput = document.getElementById('inputPasswordSignUp')
const confirmPasswordSignUpInput = document.getElementById('inputPasswordSignUpConfirm')
const signUpBtn = document.getElementById('btnSignUpForm')

const checkSignUpInputs = () => {
    signUpBtn.disabled = firstNameSignUpInput.value.length === 0 ||
        lastNameSignUpInput.value.length === 0 ||
        emailSignUpInput.value.length === 0 ||
        passwordSignUpInput.value.length === 0 ||
        passwordSignUpInput.value.length === 0 ||
        confirmPasswordSignUpInput.value.length === 0
}

firstNameSignUpInput.oninput = () => checkSignUpInputs();
lastNameSignUpInput.oninput = () => checkSignUpInputs();
emailSignUpInput.oninput = () => checkSignUpInputs();
passwordSignUpInput.oninput = () => checkSignUpInputs();
confirmPasswordSignUpInput.oninput = () => checkSignUpInputs();

checkSignUpInputs();

// Set cookie
function setCookie(name, value, days) {
    let expires = "";
    if (days) {
        let date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        expires = "; expires=" + date.toUTCString();
    }
    document.cookie = name + "=" + (value || "") + expires + "; path=/";
}

// Function for getting value from cookie
function getCookie(cookie_name) {
    let name = cookie_name + "=";
    let decodedCookie = decodeURIComponent(document.cookie);
    let ca = decodedCookie.split(';');
    for (let i = 0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) === ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) === 0) {
            return c.substring(name.length, c.length);
        }
    }
    return "";
}

// Delete temporary session from cookie
function deleteCookie(cookie_name) {
    document.cookie = cookie_name + '=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT;';
}

// Default redirect function
function afterSaveSession(response) {
    window.location.replace('/')
}

signInBtn.onclick = make_classic_login_execute;

function make_classic_login_execute(){
    let data = {
        email: document.getElementById("inputEmailSignIn").value,
        password: document.getElementById("inputPassword").value,
        actor_type: "classic_user"
    };
    make_classic_login(data)
    return false;
}

function generateQr(data, elementId){

    const qr = new VanillaQR({
        url: data,
        width: 600,
        height: 600,
        colorLight: "#ffffff",
        colorDark: "#000000",
        noBorder: true,
    });

    const imageElement = qr.toImage("png");

    if (imageElement) {
        const qr_html = document.getElementById(elementId)
        const oldQrImg = qr_html.getElementsByTagName('img')[0];

       if(oldQrImg) {
           qr_html.replaceChild(imageElement, oldQrImg)
       } else {

           switch (elementId) {
               case 'qrLogin':
                   qr_html.insertBefore(imageElement, document.getElementById('qrLoginExpired'))
                   break;
               case 'qrRegistration':
                   qr_html.insertBefore(imageElement, document.getElementById('qrRegistrationExpired'))
                   break;
               default:
                   // qr_html.innerHTML = '';
                   // qr_html.appendChild(imageElement)
           }
       }
    }
}

signUpBtn.onclick = function () {
    const data = {
        "uinfo": {
            "first_name": document.getElementById("inputFirstName").value,
            "last_name": document.getElementById("inputSurname").value
        },
        "email": document.getElementById("inputEmailSignUp").value,
        "password": document.getElementById("inputPasswordSignUp").value,
        "password_confirmation": document.getElementById("inputPasswordSignUpConfirm").value,
        "actor_type": "classic_user"
    }
    requestPostMethod('%(registration_url)s', data)
    return false;
};

function newNotify(text, type) {
    const Notify = new XNotify("TopRight");

    Notify[type]({
        title: type.charAt(0).toUpperCase() + type.slice(1),
        description: text,
        duration: 4000
    });
}

function handleErrors(response) {
    if (!response.ok) {
        return Promise.reject(response);
    }
    return response.json();
}

let requestPostMethod = (
    url,
    data,
    callback
) => {
    fetch(
        url,
        {
            method: "post",
            headers: {
                "Accept": "application / json",
                "Content-Type": "application/json"
            },
            body: JSON.stringify(data)
        }
    )
        .then(handleErrors)
        .then(result => {
            newNotify(result.message, 'success')
            if(callback){
                callback()
            }
        })
        .catch(error => {
            error.json().then((json) => {
                newNotify(json.error_message || 'Something went wrong', 'error')
            })
        })
}
