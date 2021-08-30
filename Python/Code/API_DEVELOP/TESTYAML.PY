import yaml,os
class Dict(dict):
    def __getattr__(self, key):
        value = self.get(key)
        return Dict(value) if isinstance(value,dict) else value
    def __setattr__(self, key, value):
        self[key] = value

if os.path.exists('config.yml'):
    rfile = open('config.yml','r',encoding = 'utf-8')
    dicttest = yaml.load(rfile)
    ob = Dict(dicttest)
    # print(dicttest)
    print(ob)
    name = 'apidoc'
    print(ob.name)
    print(ob[name].title)
else:
    print(2)