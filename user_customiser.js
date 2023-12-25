async function autoClick(page) {
    /**
     * Auto click on all tree items until the count of un-clicked
     * items are the same for X-many times.
     */
    await page.evaluate(async () => {
        var LAST = null;
        var STAYED_SAME_FOR = 0;
        await new Promise((resolve) => {
            var timer = setInterval(() => {
                let treeitems = document.querySelectorAll("[role=treeitem]");
                let not_yet_expanded = 0;

                for (let treeitem of treeitems) {
                    // console.log(treeitem);
                    if (
                        treeitem.querySelector("button") &&
                        !treeitem.querySelector(":scope > ul")
                    ) {
                        not_yet_expanded++;

                        let btn = treeitem.querySelector(
                            "button[aria-expanded=false]"
                        );
                        if (btn) {
                            btn.click();
                        }
                    }
                }

                if (LAST == not_yet_expanded) {
                    STAYED_SAME_FOR++;
                } else {
                    STAYED_SAME_FOR = 0;
                }
                if (STAYED_SAME_FOR >= 50) {
                    clearInterval(timer);
                    resolve();
                    console.log("resolved expansion");
                }
                LAST = not_yet_expanded;
            }, 150);
        });
    });
}

async function autoScroll(page) {
    /**
     * Auto scroll to bottom of page,
     * in order to trigger rendering of lazy-loaded content.
     */
    await page.evaluate(async () => {
        await new Promise((resolve) => {
            var totalHeight = 0;
            var distance = 1000;
            var timer = setInterval(() => {
                var scrollHeight = document.body.scrollHeight;
                window.scrollBy(0, distance);
                totalHeight += distance;

                if (totalHeight >= scrollHeight - window.innerHeight) {
                    clearInterval(timer);
                    resolve();
                }
            }, 500);
        });
    });
}

exports.setPageOptionsPre = async (page, options) => {
    // console.log(`> setPageOptionsPre`);
    await page.setRequestInterception(true);
    page.on("request", (interceptedRequest) => {
        if (interceptedRequest.isInterceptResolutionHandled()) return;

        const isMatched = /ContentViewedEventQuery/.test(interceptedRequest.url());
        if (isMatched) {
            // Make a new call

            let new_url = interceptedRequest.url().replace(/,?\bContentViewedEventQuery\b/, '').replace(/=,/, '=')
            // console.log(new_url);

            // if (interceptedRequest.url().includes("some-string")) {
            interceptedRequest.respond({
                status: 302,
                headers: {
                    location: new_url,
                },
            });
            //   console.log(interceptedRequest.url());
        } else {
            interceptedRequest.continue();
        }
    });
}

exports.pageGotoPre = async (page, options) => {
    // console.log(`> pageGotoPre`);
    console.log(`> Getting ${options.url}`);
}

exports.pageGotoPost = async (page, options) => {
    // console.log(`> pageGotoPost`);
    await Promise.all([autoClick(page), autoScroll(page)]);
}