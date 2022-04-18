function SetServiceCookie(msg) {
    if (msg["session_token"] !== undefined) {
        %s
        saveSession(msg);
    }
}