SJSON
=====

**SJSON** is a small library to read/write simplified JSON, as described originally on the [Bitsquid blog](http://bitsquid.blogspot.de/2009/10/simplified-json-notation.html).

License
-------

**SJSON** is licensed under the two-clause BSD license. See ``LICENSE.txt`` for details.

SJSON format
------------

SJSON is very similar to normal JSON. It mostly reduces the required markup a bit.

* File starts with an implicit object. That is, an empty SJSON file is equivalent to a JSON file containing ``{}``.
* Commas after a key-value pair are optional.
* Keys don't have to be quoted as long as they are valid identifiers.
* ``=`` is used instead of ``:``

Example
-------

JSON:

    {
        "foo" : 23,
        "bar" : [1, 2, 3],
        "baz" : {
            "key" : "value"
        }
    }

SJSON:

    foo = 23
    bar = [1, 2, 3]
    baz = {
        key = "value"
    }

As an extension, SJSON allows for raw string literals.

    foo = [=[This is a raw literal with embedded " and stuff]=]

Usage
-----

The library provides two methods, ``dumps`` and ``loads``. ``dumps`` encodes an object as SJSON, and ``loads`` decodes a string into a Python dictionary.
