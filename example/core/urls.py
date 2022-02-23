from app.apis import logout

# ClassBase or function_base (if function_base, how should we handle decorators, seperate or all together?)
urls = {
    '': Class2.api(),
    'logout/': logout,
    'user/': {
        '<int>/': SingleUser.api(),
        'lists/': UsersList.api(),
    }
}
# He can import another dict as url here
