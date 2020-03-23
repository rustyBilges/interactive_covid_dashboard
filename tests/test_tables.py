import pytest 

@pytest.mark.parametrize('path', (
    '/',
    '/table2',
    '/submit_table1',
    '/submit_table2'
))
def test_login_required(client, path):
    response = client.get(path)
    assert response.headers['Location'] == 'http://localhost/auth/login'

def test_submit_table1(client, auth):
    ## test that it redirects to table 2 AND 
    ##              saves table 1 data correctly 
    auth.login()
    response = client.post('/submit_table1')
    assert response.headers['Location'] == 'http://localhost/table2'
    
def test_submit_table2(client, auth):
    ## test that it redirects to logout message AND 
    ##              saves table 2 data correctly 
    auth.login()
    response = client.post('/submit_table2')
    assert response.headers['Location'] == 'http://localhost/logout_msg'
    
