CSVFILES=$(wildcard reports/*.csv)
VALID=valid.txt

clean:
	echo "Make: Cleaning reports directory"
	(rm reports/bad_*)
	(rm reports/report_*)
check: $(CSVFILES)
	echo "Make: Checking time data"
	python validate_toggl.py $^ $(VALID) 