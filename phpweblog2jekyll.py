#!/usr/bin/env python
#
# Convert a phpweblog database export into files for use with Jekyll
# 
import csv, sys, os, datetime, re, optparse
from BeautifulSoup import BeautifulSoup
from html2markdown import html2markdown

## Default settings, these are what I use. 
## either edit in-place or create a file called local_settings.py

# These map phpweblog category ids to category names
categories = {
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

######### Only used if you generate redirects: 
phpweblog_url_pattern = '/diary/(index.php)?'
jekyll_base_url = 'http://www.gdb.me'

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

def entries_from_csv(csvfile, skipped_entries):
    """Generate entries from CSV database export."""

    fieldnames = ["eid", "title", "catid", "createtime", "updatetime", "teaser", "more"]
    reader = csv.DictReader(open(csvfile), fieldnames=fieldnames, delimiter=';',
                escapechar='\\')
    
    for row in reader:
        if row['eid'] in skipped_entries:
            continue

        entry = {}
        
        entry['eid'] = row['eid']
        entry['title'] = row['title']
        entry['created'] = datetime.datetime.fromtimestamp(int(row["createtime"]))
        entry['updated'] = datetime.datetime.fromtimestamp(int(row["updatetime"]))
        entry['cleaned_filename'] = title_to_filename(entry['title'])
    
        entry['html'] = row["teaser"]
        if row.has_key("more"):
            entry['html'] += row['more']

        try:
            entry['category'] = categories[int(row["catid"])]
        except KeyError:
            sys.stderr.write('WARNING: No category mapping found for category id %s, assigning to default\n'
                % row['catid'])
            sys.stderr.write('Edit local_settings.py and add a categories map.\n')
            entry['category'] = 'default'
    
        yield entry

def write_entry_as_markdown(entry, postsdir):
    filename = '%s-%s.md' % (entry['created'].strftime("%Y-%m-%d"), entry['cleaned_filename'])
    filepath = os.path.join(postsdir, filename)

    body = tidy_html(entry['html'], relative_links_url)
    (junk, md) = html2markdown(body)
    md = tidy_markdown(md) 

    if entry['updated'] > (entry['created'] + datetime.timedelta(minutes=5)):
       updatestring = 'updated: %s\n' % entry['updated'].strftime("%Y-%m-%d")
    else:
       updatestring = ''

    f = open(filepath, 'w')
    f.write('---\ntitle: \"%s\"\ncategory: %s\nlayout: default\nweblog_eid: %s\n%s---\n' 
        % (entry["title"], entry['category'], entry['eid'], updatestring))
    f.write(md)
    f.close()

def write_redirect(entry, redirect_file, old_url, new_host):
    redirect_file.write('\n# Redirect: %s\n' % entry['title'])
    redirect_file.write('RewriteCond %%{QUERY_STRING} wl_eid=%s([^\d]|$)\n' % entry['eid'])
    redirect_file.write('RewriteRule %s %s/%s/%s.html? [L,R=301]\n' 
        % (old_url, new_host, entry['category'], entry['cleaned_filename']))

if __name__ == '__main__':

    optparser = optparse.OptionParser()
    optparser.add_option('-r', '--redirect-file', dest='redirect_file', help='Write redirects to FILE', 
        type="string", default=None)
    (opts, args) = optparser.parse_args()

    try:
       postsdir = args[1]
    except IndexError:
       postsdir = '.'

    if opts.redirect_file:
        redirect_file = open(opts.redirect_file, 'w')

    for entry in entries_from_csv(args[0], skipped_entries):
        write_entry_as_markdown(entry, postsdir)
        if opts.redirect_file:
            write_redirect(entry, redirect_file, phpweblog_url_pattern, jekyll_base_url)

