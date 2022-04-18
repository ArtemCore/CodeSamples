# Usage guide and samples of ecosystem54 submodule for enterpise level projects

## 1. Replacing submodule endpoints

#### In case when service needs to have custom views or even urls instead of submodule realization, developer may follow the steps described below

For example, service will have custom authorization view and url.
In such case, we have to get rid of standart '/authorization/' endpoint without changing submodule code.

To complete this, developer needs
 - add to app config SKIP_SUBMODULE_ENDPOINTS list with value ['auth_submodule.authorization']
 - use AuthPermsFlask intead of standart Flask class during defining app object
    ```python
    from submodules.auth_perms import AuthPermsFlask

    app = AuthPermsFlask(
        __name__,
        static_url_path='/static',
        static_folder='static',
        template_folder='templates',
    )
    ```


## 2. Custom Classic user SignIn/SignUp

#### You can create any template for SignIn/SignUp if you need and use provided js functionality from ecosystem54 submodule.
#### All what you need is
 - include html templates with scripts for SignIn/SignUp (or both)
    ```html
    {% include 'auth_enterprise/classic_login.html' %}
    {% include 'auth_enterprise/classic_registration.html' %}
    ```
 - complete any custom js to get data from your template
 - call included functions
    ```js
    AuthClassicSignIn(email, password);
    // or
    AuthClassicSignUp(first_name, last_name, email, password, password_confirmation, need_sign_in);
    ```
 - replace standart functions if you need with any custom logic
    ```js
    // redirecting to '/' by default
    // common for classic and QR SignIn and for SSO function
    function afterSaveSession(response) {
        window.location.replace("{{ url_for('ANY ENDPOINT') }}");
    }
    // Sign In functions
    function handleSignInError(response) {
        alert('Something went wrong during Sign In'); 
    }

    // Sign Up functions
    function handleSignUpSuccess(response) {
        alert('Successfully registered');
    }

    function handleSignUpError(response) {
        alert('Something went wrong during Sign Up');
    }

    // Must have Promise inside to be sure that all logic or requests was finished
    // before next steps processing
    // common for classic and QR SignUp function
    function afterSignUp(response) {
        return new Promise(((resolve, reject) => {
            //any logic
            resolve();
        }))
    }
    ```    


## 3. Custom Qr code SignIn/SignUp

#### As for classic users, you can create any custom templates for SignIn/SignUp with QR code (if standalone mode in not active)

 - include html template with scripts for QR code logic
    ```html
    {% include 'auth_enterprise/qr_code.html' %}
    ```

 - set values to next variables
    ```js
    // parent blocks for inserting QR code
    LoginQrWrapperID = 'qrLogin';
    RegistrationQrWrapperID = 'qrRegistration';
    // period when the SignIn request will be sent (in sec)
    LoginQrTimeRange = 45; // default 
    // period when the SignUp request will be sent (in sec)
    RegistrationQrTimeRange = 120; // default
    ```
 - call inculed functions whenever you want to insert and start processing of QR code
    ```js
    // or 'registration'
    getQrCode('authentication');
    ```
 - replace standart functions if you need with any custom logic
    ```js
    // or insertRegistrationQrCode
    function insertLoginQrCode (qr_wrapper, imageElement) {
        // imageElement is ready for inserting QR code image
        // any logic
    }

    // or changeVisibilityRegistrationQrCode
    function changeVisibilityLoginQrCode(hide) {
        // hide is true or false
        //any logic
    }

    // functions afterSaveSession and afterSignUp
    // described on step 2
    ```

## 4. Custom Sinle-Sign-On with Auth service (SSO)

#### This case gives an ability to receive session from Auth service (if or until it exists) and create a new one on you service

 - include html template with scripts for SSO
    ```html
    {% include 'auth_enterprise/single_sign_on.html' %}
    ```

 - call included function whenever you want to make SSO
    ```js
    makeSSOLogin();
    ```



## 5. Usage near alembic migrations

#### If your project use alembic migrations (for SQLAlchemy ORM), 
#### by default all ecosystem54 submodule tables will be removed during any alembic migrations creation process.

#### To avoid this, you should modify you alembic configuration (inside migrations folder by default)
 - add such data into your alembic.ini file
    ```
    [submodule]
    tables_name = migrations,actor,service_session_token,temporary_session,permissions,salt_temp,invite_link,invite_link_temp,phantom_relation,default_permaction,actor_permaction,group_permaction
    ```
 - add such code into env.py file
    ```python
    try:
        submodule_tables_name = config.get_section('submodule').get('tables_name').split(',')
    except (TypeError, AttributeError):
        submodule_tables_name = []

    def include_object(object, name, type_, reflected, compare_to):
        if type_ == 'table' and name in submodule_tables_name:
            return False
        return True
    ...
    # inside run_migrations_online functions add include_object 
    # to context.configure arguments like
    def run_migrations_online():
        ...
        context.configure(
                connection=connection,
                target_metadata=target_metadata,
                process_revision_directives=process_revision_directives,
                include_object=include_object,
                **current_app.extensions['migrate'].configure_args
            )

    ```   