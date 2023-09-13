# Makefile contents here
CC = g++
CFLAGS = -Wall

.PHONY : run
run:
	@./server/server &
	python3 client/client.py 

.PHONY : clean
clean:
	@-rm inpipe outpipe