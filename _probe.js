
(function(){
  function getCookie(n){var v='; '+document.cookie,p=v.split('; '+n+'=');return p.length==2?p.pop().split(';').shift():'';}
  function req(m,u,b){
    var x=new XMLHttpRequest();x.open(m,u,false);x.withCredentials=true;
    var xsrf=getCookie('_xsrf');
    if(xsrf) x.setRequestHeader('X-XSRFToken', xsrf);
    if(b){x.setRequestHeader('Content-Type','application/json');x.send(JSON.stringify(b));}
    else x.send();
    return m+' '+u+' xsrf='+!!xsrf+' => '+x.status+' '+x.responseText.slice(0,200);
  }
  var p={"type": "notebook", "content": {"cells": [{"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [], "source": ["print('hello from xsrf test')\n"]}], "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}}, "nbformat": 4, "nbformat_minor": 4}};
  var b='/user/615774912/api/contents/';
  return [
    'cookie='+document.cookie.slice(0,200),
    req('PUT', b+'Untitled.ipynb', p),
    req('POST', b+'Untitled.ipynb', p),
    req('PUT', b+'test_auto.ipynb', p)
  ].join('
');
})()
