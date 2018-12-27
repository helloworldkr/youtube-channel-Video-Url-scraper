import scrapy
import re
import pickle
import json
import sys

class MySpider(scrapy.Spider):
    global allUrlFile , fullUrl
    allUrlFile = open('allUrl.txt', 'a')
    fullUrl = open('fullUrl.txt', 'a')
    localHost = "http://localhost:8050/render.html?url="    #
    # youtubeUrl = "https://www.youtube.com/channel/UCv1Ybb65DkQmokXqfJn0Eig/channels" # channel with only one ajax    #
    # youtubeUrl = "https://www.youtube.com/user/khanacademy/videos" # khan academy
    youtubeUrl = "https://www.youtube.com/channel/UCe83jLdZ3PuqVwAHe6B3U2A/videos" #tutor2u
    start_urls = [localHost + youtubeUrl]
    name = "allvideos"

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, self.parse)

    def parse(self, response):
        self.log("this program just visited "+ response.url)


        if not 'browse_ajax' in response.url:
            data = re.findall('"continuations":\[{"nextContinuationData"(.+?)\]', response.body.decode("utf-8"), re.S)
            print("data is ")
            print(data)
            strData = data[0]#.decode("utf-8")

            filename = "continuationToken.txt"
            with open(filename, 'wb') as f:
                pickle.dump((strData), f)

            # pattern =r"continuation\":\"(\w+)"
            pattern = r"continuation\":\"(.*)\","
            continuationToken = re.search(pattern, strData ,  re.MULTILINE ).group(1)
            # print(continuationToken)
            hrefsInMainBody = []
            hrefsInMainBody = (response.css('a.yt-simple-endpoint.inline-block.style-scope.ytd-thumbnail::attr(href)').extract())
            hrefsInMainBody = [element.encode('ascii', 'xmlcharrefreplace') for element in hrefsInMainBody] # changing each element from unicode to String
            print("\n href is /////////////////////////\n")
            print(hrefsInMainBody)
            print("\n href ends \\\\\\\\\\\\\\\\\\\\\\\\\\\ \n")

            for item in hrefsInMainBody:
                #remove /watch?v=
                item = item.decode("utf-8")
                i = item.find('=')
                print(item + " and adding " + item[i+1:])
                allUrlFile.write("%s\n" % item[i+1:])
                fullUrl.write("%s\n" % item[i+1:])
                fullUrl.write("%s\n" % item)

            # call another function to fetch pending channel names from youtube of scroll equivalent
            scrollUrl = "https://www.youtube.com/browse_ajax?ctoken=" + continuationToken
            finalScrollUrl = scrollUrl
            print("final scroll url \n" + finalScrollUrl)
            yield scrapy.Request(finalScrollUrl, callback=self.parse)
        else : #ajax scroll call
            print("this is else ")
            jsonResponse = json.loads(response.text)
            # print(jsonResponse['content_html'] + "  lolaaaa")
            loadMoreDatafromHtml = jsonResponse['load_more_widget_html']
            htmlInAjaxCall = jsonResponse['content_html']


            #get hrefs of current ajax call
            hrefsInAjaxCallPattern = r"/watch\?v=.*?.\""
            try:
                # print("inside try")
                hrefsinAjaxCall = re.findall(hrefsInAjaxCallPattern , htmlInAjaxCall)
                hrefsinAjaxCall = [element.encode('ascii', 'xmlcharrefreplace')
                for element in hrefsinAjaxCall]
                hrefsinAjaxCall = list(set(hrefsinAjaxCall)) # removing duplicates using set
                for item in hrefsinAjaxCall:
                    # print("inside loop "+ item.decode('utf-8'))
                    item = item.decode('utf-8')
                    i = item.find('=')
                    # print("checking "+ item)
                    allUrlFile.write("%s\n" % item[i + 1:-1])
                    fullUrl.write("%s\n" % item)
                    fullUrl.write("%s\n" % item[i + 1:])
            except Exception as e:
                print("got caught in exception")
                print(e)
                print("ajax call urls")
            print(hrefsinAjaxCall)
            if loadMoreDatafromHtml:
                pattern = 'data-uix-load-more-href="(\/.+?)"' #getting next href for scroll
                continuationhref = re.search(pattern, loadMoreDatafromHtml).group(1)
                scrollUrl = "https://www.youtube.com" + continuationhref
                finalScrollUrl = scrollUrl
                print("final scroll url \n" + finalScrollUrl)
                yield scrapy.Request(finalScrollUrl, callback=self.parse)
            else:
                print("empty load more data")
