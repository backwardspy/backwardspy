| album | track | artist | album |
| - | - | - | - |
{%for t in entries%}
| <img src="{{t.album.images[-1].url}}" width="48" height="48"> | [{{t.name}}]({{t.external_urls.spotify}}) | {%for artist in t.artists%}[{{artist.name}}]({{artist.external_urls.spotify}}){%if not loop.last%}, {%endif%}{%endfor%} | [{{t.album.name}}]({{t.external_urls.spotify}}) |
{%endfor%}