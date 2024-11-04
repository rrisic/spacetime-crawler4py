count = 0
with open('./Logs/subdomain_page_count.txt') as subpage_txt:
    SUBDOMAIN_PAGE_COUNT = {}
    while True:
        new_line = subpage_txt.readline().split(', ')
        if (new_line == [""]):
            break
        SUBDOMAIN_PAGE_COUNT[new_line[0]] = int(new_line[1])

for key in sorted(SUBDOMAIN_PAGE_COUNT):
    count += 1
    print(f'	{key}, {SUBDOMAIN_PAGE_COUNT[key]}')
print(count)
print(len(SUBDOMAIN_PAGE_COUNT))
