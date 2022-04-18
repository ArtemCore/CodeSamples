fetch(
    "%s/auth/",
    {
        method: "post",
        headers: {
            "Accept": "application/json",
            "Content-Type": "application/json"
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        if (response.ok) {
            response.json().then((response) => {
                document.cookie = "%s=" + response["session_token"] + "; path=/";
                if (response.redirect_to) {
                    window.location = response.redirect_to;
                }
                else {
                    %s
                }
            })
        } else {
            response.json().then((json) => {
                newNotify(json.error_message || 'Something went wrong', 'error')
            })
        }
    })
