# SPDX-License-Identifier: GPL-2.0
CFLAGS_trace.o := -I$(src)

obj-m += tps6598x-core.o
tps6598x-core-y := core.o
tps6598x-core-$(CONFIG_TRACING) += trace.o
