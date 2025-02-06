This AWS Lambda package contains a function that scrapes multiple news sources for the latest Cyber Threats.
The last scraped article tiles are saved to an S3 bucket and retrieved at the start of the next function run.
The titles are compared to the latest scraped articles to make sure duplicates are not sent through.
The function sends links to the publishing website to an instant messaging chat which can be seen by engineers
Once the function has completed its cycle the laste article titles are then written to the text file in the S3 bucket, ready for the next iteration.