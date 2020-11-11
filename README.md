# Python-EveryThing-SDK
https://www.voidtools.com/support/everything/sdk/

```py
everything = Everything()
# sets the search options
everything.set_search('everything')
everything.set_request_flags(EVERYTHING_REQUEST_FULL_PATH_AND_FILE_NAME|EVERYTHING_REQUEST_DATE_MODIFIED)
# starts the search
everything.query()
# prints all results
for i in range(everything.get_result_count()):
    print(everything.get_result(i))
    print('Modified date: %s' % everything.get_result_date(i,'Modified'))
    print()
# if there is a function that is not implemented in the class, use:
# https://www.voidtools.com/support/everything/sdk/everything_getmatchcase/
everything.set_args('GetMatchCase', BOOL)  # function name, result type, *arg types
match_case = everything.GetMatchCase()
print(f'Match case: {match_case}')
```
