from urllib.parse import urlencode, urlparse, urlunparse, parse_qs, urldefrag

def ensure_absolute_link(link):
    if link.startswith('/'):
        return "https://www.goodreads.com" + link
    return link

def ensure_rel_link(link):
    if link.startswith('https://www.goodreads.com'):
        return link.removeprefix('https://www.goodreads.com')
    return link

def format_link(link):
    # Remove 'ref' query and fragment
    parsed_url = urlparse(link)
    query_params = parse_qs(parsed_url.query)
    query_params.pop('ref', None)
    parsed_url = parsed_url._replace(query=urlencode(query_params, True))
    return urldefrag(urlunparse(parsed_url))[0]

def is_book(link):
    link = ensure_rel_link(link)

    sections = link.split("/")
    if len(sections) == 4 and sections[1] == "book" and sections[2] == "show":
        return True
    return False