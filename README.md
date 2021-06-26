# Python-EveryThing-SDK
https://www.voidtools.com/support/everything/sdk/

```py
everything = Everything()
# sets the search options
everything.set_search('everything')
everything.set_request_flags(Request.FullPathAndFileName|Request.DateModified|Request.Size)
# starts the search
if not everything.query():
    raise Exception(everything.get_last_error())
# prints all results
for item in everything:
    print(
        item.get_filename(),
        f'Size: {item.get_size()} Bytes',
        f'Modified date: {item.get_date_modified()}',
        '', sep='\n'
    )
```
