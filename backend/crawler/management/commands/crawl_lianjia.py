from django.core.management.base import BaseCommand

from crawler.spiders.lianjia import LianjiaSpider


class Command(BaseCommand):
    help = "Crawl Xi'an Gaoling District house data from lianjia.com"

    def add_arguments(self, parser):
        parser.add_argument(
            "--max-pages",
            type=int,
            default=15,
            help="Maximum number of pages to crawl (default: 15)",
        )
        parser.add_argument(
            "--delay",
            type=float,
            default=2.0,
            help="Delay between requests in seconds (default: 2.0)",
        )
        parser.add_argument(
            "--no-headless",
            action="store_true",
            default=False,
            help="Show browser window for login (default: headless mode)",
        )

    def handle(self, *args, **options):
        spider = LianjiaSpider(
            max_pages=options["max_pages"],
            delay=options["delay"],
            headless=not options["no_headless"],
        )
        spider.stdout_write = lambda msg: self.stdout.write(msg)

        self.stdout.write(
            self.style.WARNING(
                f"Starting lianjia crawler: max_pages={options['max_pages']}, "
                f"delay={options['delay']}s, "
                f"headless={not options['no_headless']}"
            )
        )

        stats = spider.run()

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Crawl complete: "
                f"{stats['pages_fetched']} pages fetched, "
                f"{stats['items_parsed']} items parsed, "
                f"{stats['items_saved']} saved, "
                f"{stats['items_skipped']} skipped, "
                f"{stats['errors']} errors"
            )
        )
