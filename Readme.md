
# Export blog posts from phpweblog to Jekyll

## Why use it?

You've decided to migrate a blog from phpweblog to
[Jekyll](http://www.jekyllrb.com/) and you want to take your old blog posts
with you.

## What does it do?

This script reads a CSV file export of the phpweblog database and produces:

- A Markdown file for each blog post
- Optionally, a file containing mod_rewrite rules to redirect the old content to the content.

## What doesn't it do?

It doesn't work very well. It's bad at reading poorly marked-up HTML, because 
html2markdown, which it uses to convert HTML to Markdown, isn't very good at that.

Specific problems that I have come across are:
- lists inside <p> tags
- blockquotes inside <p> tags that contain other text

In addition to things that cause it to fail outright, it also produces Markdown that
maruku (the markdown compiler jekyll uses by default) dislikes, generally because
spaces get inserted between markup and content.

There are some extremely hacky workarounds for this in phpweblog2jekyll, which 
essentially run regexes on the Markdown, fixing the problems that prevented my blog
posts compiling cleanly.

### Why did you bother releasing it, then?

It's still probably easier than importing/converting posts manually and there's a
chance that it might be moderately helpful in writing another tool.

## How do I use it?

### Installing

- You'll need python >= 2.7
- Get a copy of [html2markdown](http://www.codefu.org/html2markdown/)
- Copy the htmlmarkdown.py file into a directory
- Download a copy of phpweblog2jekyll.py and place it in the same directory

### Using

Run the script thus: 

	phpweblog2jekyll csvfile [postsdir] 

For example:

	phpweblog2jekyll gdb_diary.csv _posts

It will generate a .md file containing [Jekyll's YAML front
matter](https://github.com/mojombo/jekyll/wiki/YAML-Front-Matter) for each post
found in the CSV file. The files will be named in the format Jekyll expects
posts to be named: %Y-%m-%d-title.md, so you should be able to simply run
jekyll afterwards and have it generate your posts.

#### Metadata

Some additional metadata will be added to the YAML front matter in each file:

- phpweblog_eid: contains the phpweblog entry id (eid). This is useful for working
out where a post came from
- updated_at: if the post was edited more than 5 minutes after creation, this field will be added and will contain the date of the edit in %Y-%m-%d format

#### Generating redirects

When you've migrated and generated your posts, you'll probably want to add some 
redirects from the old posts to the new ones. If you're hosting the old site under
Apache httpd and mod_rewrite is available you can generate s file containing
RewriteRules that should make all the necessary redirects.

	phpweblog2jekyll -u origurl -d desturl -r redirectfile csvfile [postsdir]

For example:

	phpweblog2jekyll -u '^/diary/' -d 'http://www.gdb.me/' -r blog-redirects.conf \
	gdb_diary.csv _posts

Be warned that his will also output files to the posts directory, overwriting any changes
you made since a previous conversion.

The redirect generator assumes that you're using 'permalink: none' in your
_config.yaml. If this is not the case, then you'll need to either patch the code
or write something to generate redirects from the phpweblog_eid YAML data.

## How do I report bugs?

Since I don't have any further need for this code, it's unlikely that I'll be
particularly motivated to investigate bugs. However, if you find and fix a bug,
please send a pull request on github.
