#!/usr/bin/env python
#
# Convert a phpweblog database export into files for use with Jekyll
# 
import csv, sys, os, datetime, re
from BeautifulSoup import BeautifulSoup
from html2markdown import html2markdown

## Default settings, these are what I use. 
## either edit in-place or create a file called local_settings.py

# These map phpweblog category ids to category names
category_to_tags = {
    1: "miscellaneous",
    2: "website",
    3: "Australia",
    4: "travel",
    5: "computing",
    6: "London",
    7: "smoking",
    8: "windsurfing",
    9: "photos",
}

# If set, this fully qualifies relative links by prepending the string below
# set it to '' to disable this.
relative_links_url = 'http://www.darkskills.org.uk'

# If you want to skip imports of a few entries, put their ids in a list
# skipped_entries = [99, 100]
skipped_entries = []

# 

## End of default settings

try:
    from local_settings import *
except ImportError:
    sys.stderr.write('WARNING: no local_settings.py found, using defaults.\n')

def tidy_html(html, rel_url=''):
    """Modify the HTML in the following ways:
        - fully qualify unqualified links with <hostname>
        - prettify the HTML."""

    try:
        soup = BeautifulSoup(html)
    except: 
        print html
        raise 

    for tag in soup.findAll("img"):
        if tag["src"].startswith("/"):
            tag["src"] = rel_url + tag["src"]
        
    for tag in soup.findAll("a"):
        try:
            if tag["href"].startswith("/"):
                tag["href"] = rel_url + tag["href"]
        except KeyError:
            print "WARNING parse error: " + tag.prettify()
    
    return soup.prettify()

def title_to_filename(title):
    """Given a string title, make a sane filename from it (no whitespace, lowercase,
    certain punctuation characters removed)."""
    sane_title = title.replace('...','')
    sane_title = sane_title.strip()
    sane_title = sane_title.replace(" ",'-')
    sane_title = re.sub(r"""[\:\.\,\!'\?]""",'', sane_title)
    sane_title = sane_title.lower()
    return sane_title

def tidy_markdown(md):
    """Fix a few complaints from the maruku markdown compiler."""
    # Remove spaces between _, **, ## and words.
    (md, changes) = re.subn(r"""\_\s+(\w[^\_]+)\s+\_""", r"""_\1_""", md, 0, re.MULTILINE)
    (md, changes) = re.subn(r"""\*\*\s+(\w[^\*]+)\s+\*\*""", r"""**\1**""", md, 0, re.MULTILINE)
    (md, changes) = re.subn(r"""(#+)\s{2,}(\w[^#]+)\s{2,}(#+)""", r"""\1 \2 \3""", md, 0, re.MULTILINE)
    # Fix literal square brackets that don't get escaped
    (md, changes) = re.subn(r"""\[([^\]]+)\]([^\(])""", r"""\\[\1\\]\2""", md, 0, re.MULTILINE)
    # Remove spurious spaces between closing anchors and punctuation
    (md, changes) = re.subn(r"""(\))\s+([\.\?\!\,])""", r"""\1\2""", md, 0, re.MULTILINE)
    
    # Fix a specific issue with image URLs    
    (md, changes) = re.subn(r"""\((\w+)\)\.([Jj][Pp][Gg])""", r"""%28\1%29.\2""", md)

    return md

fieldnames = ["eid", "title", "catid", "createtime", "updatetime", "teaser", "more"]
reader = csv.DictReader(open(sys.argv[1]), fieldnames=fieldnames, delimiter=';',
            escapechar='\\')

redirect_file = sys.stdout

for entry in reader:
    created = datetime.datetime.fromtimestamp(int(entry["createtime"]))
    updated = datetime.datetime.fromtimestamp(int(entry["updatetime"]))

    if updated > (created + datetime.timedelta(minutes=5)):
        updatestring = 'updated: %s\n' % updated.strftime("%Y-%m-%d")
    else:
        updatestring = ''

    if entry['eid'] in skipped_entries:
        continue

    html = entry["teaser"]
    if entry.has_key("more"):
        html += entry['more']
    body = tidy_html(html, relative_links_url)
    tag = category_to_tags[int(entry["catid"])]
    (junk, md) = html2markdown(body)
    md = tidy_markdown(md) 

    try:
        dirname = sys.argv[2]
    except IndexError:
        dirname = '.'

    title_filename = title_to_filename(entry['title'])

    filename = '%s-%s.md' % (created.strftime("%Y-%m-%d"), title_filename)
    filepath = os.path.join(dirname, filename)

    f = open(filepath, 'w')
    f.write('---\ntitle: \"%s\"\ncategory: %s\nlayout: default\nweblog_eid: %s\n%s---\n' 
        % (entry["title"], tag, entry['eid'], updatestring))
    f.write(md)
    f.close()

    redirect_file.write('\n# Redirect: %s\n' % entry['title'])
    redirect_file.write('RewriteCond %%{QUERY_STRING} wl_eid=%s([^\d]|$)\n' % entry['eid'])
    redirect_file.write('RewriteRule /diary/(index.php)? http://www.gdb.me/%s/%s.html? [L,R=301]\n' % (tag, title_filename))
