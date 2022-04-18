function saveSession(data) {
    fetch(
        "%s/save_session/",
        {
            method: "post",
            headers: {
                "Accept": "application/json",
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                session_token: data.%ssession_token
            })
        }
    ).then(response => {
        response.json().then((json) => {
            document.cookie = "%s=" + data.%ssession_token + "; path=/";
            if (json.redirect_to) {
                window.location = json.redirect_to;
            }
            else {
                %s
            }
        })
    })
}