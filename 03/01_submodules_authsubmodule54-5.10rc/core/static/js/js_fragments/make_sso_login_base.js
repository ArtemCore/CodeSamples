function make_sso_login(){
    let data = {
        uuids: [],
        sessions: [],
        services: [],
        redirect_url: window.location,
    };
    fetch( "%s/auth_sso_generation/" )
    .then(response => {
        response.json().then((response) => {
            data.uuids.push(response.uuid);
            data.sessions.push(response.session);
            document.cookie = "temporary_session=" + response["session"] + "; path=/";
            %s
        });
    });
    return false;
};