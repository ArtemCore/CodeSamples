fetch("%s/auth_sso_generation/")
    .then(response => {
        response.json().then((response)=>{
            data.uuids.push(response.uuid);
            data.sessions.push(response.session);
            data.services.push(response.service);
            document.cookie = "temporary_session_%s=" + response["session"] + "; path=/";
            %s
        });
    });