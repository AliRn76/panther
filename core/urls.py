



urls = {
    '': Class2.api(),
    'logout/': Logout.api(),
    'user/': {
        '<int>/': SingleUser.api(),
        'lists/': UsersList.api(),
    }
}
# He can import another dict as url here
