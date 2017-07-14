/* vim:set ft=c ts=2 sw=2 sts=2 et cindent: */

/*
 * Usage info after license block.
 *
 * This code is by Peter Silva copyright (c) 2017 part of MetPX.
 * copyright is to the Government of Canada. code is GPL.
 *
 * based on a amqp_sendstring from rabbitmq-c package
 * the original license is below:
 */

/* 
  Minimal c implementation to allow posting of sr_post(7) messages.

  call an sr_context_init to set things up.
  then sr_post will post files,
  then sr_close to tear the connection down.

  there is an all in one function: connect_and_post that does all of the above.

 */

#include "sr_context.h"

struct sr_message_t {
  char exchange[AMQP_MAX_SS];
  char routing_key[AMQP_MAX_SS];
  char queue[AMQP_MAX_SS];
  char to_clusters[AMQP_MAX_SS];
  char from_clusters[AMQP_MAX_SS];
  char atime[SR_TIMESTRLEN];
  char mtime[SR_TIMESTRLEN];
  int  mode;
  char parts_s;
  long parts_blksz;
  long parts_blkcount;
  long parts_rem;
  long parts_num;
  char sum[SR_SUMSTRLEN];
  char datestamp  [SR_TIMESTRLEN];
  char url[PATH_MAX];
  char path[PATH_MAX];

  // sr_report(7) fields.
  int statuscode;
  char consumingurl[PATH_MAX];
  char consuminguser[PATH_MAX];
  float duration;

};

//extern struct sr_message_t msg;


void sr_consume_init(struct sr_context *sr_c);
/* 
   declare and bind queue over a connection already established by context_init


 */

void sr_message_2json(struct sr_message_t *m);
/* 
   print a message to stdout
 */
struct sr_message_t *sr_consume(struct sr_context *sr_c);

 
