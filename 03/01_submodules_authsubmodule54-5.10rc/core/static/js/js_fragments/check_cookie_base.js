function checkCookie() {
    let temporary_session = {
        %s
    }
    if(temporary_session.temporary_session) {
        %s
        getSessionByTemporaryToken(temporary_session);
    }
    if(getCookie("%s")){
        // window.location.reload();
    }
}

function getSessionByTemporaryToken(temporary_session) {    
    const getToken = async () => {
        try {
            const response = await fetch('%s', {
                method: 'POST',
                headers: {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
                body: JSON.stringify(temporary_session)
            });
            if (response.status === 200) {
                const serviceCookie = await response.json();
                SetServiceCookie(serviceCookie['session_token'])
            }
        } catch (err) {
            console.log(err);
        }
    }
    getToken();
}
