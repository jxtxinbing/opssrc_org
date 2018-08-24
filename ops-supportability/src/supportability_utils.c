/*
 *  (c) Copyright 2016 Hewlett Packard Enterprise Development LP
 *  Copyright (c) 2008, 2009, 2010, 2011, 2012, 2013, 2014 Nicira, Inc.
 *
 *  Licensed under the Apache License, Version 2.0 (the "License"); you may
 *  not use this file except in compliance with the License. You may obtain
 *  a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Unless required by applicable law or agreed to in writing, software
 *  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 *  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 *  License for the specific language governing permissions and limitations
 *  under the License.
 */

/************************************************************************//**
 * @ingroup ops-supportability
 *
 * @file
 * Source file for the supportability common utils
 ***************************************************************************/


#include <errno.h>
#include <unistd.h>
#include "jsonrpc.h"
#include "openvswitch/vlog.h"
#include "util.h"
#include "unixctl.h"
#include "dirs.h"

#include "supportability_utils.h"
#include "supportability_vty.h"

#define REGEX_COMP_ERR        1000
#define MAX_PID               65536
#define MIN_PID               1
#define MAX_PID_LEN           5
#define MIN_PID_LEN           1


VLOG_DEFINE_THIS_MODULE (supportability_utils_debug);


static int read_pid_file (char *pidfile);


/* Function        : strncmp_with_nullcheck
 * Responsibility  : Ensure arguments are not null before calling strncmp
 * Return          : -1 if arguments are null otherwise return value from
 *                    strncmp
 */
int
strncmp_with_nullcheck( const char * str1, const char * str2, size_t num )
{
  if(str1 == NULL || str2 == NULL)
    return -1;
  return strncmp(str1,str2,num);
}





/* Function        : strcmp_with_nullcheck
 * Responsibility  : Ensure arguments are not null before calling strcmp
 * Return          : -1 if arguments are null otherwise return value from
 *                   strcmp
 */
int
strcmp_with_nullcheck( const char * str1, const char * str2 )
{
  if(str1 == NULL || str2 == NULL)
    return -1;
  return strcmp(str1,str2);
}



/* Function        : strdup_with_nullcheck
 * Responsibility  : Ensure arguments are not null before calling strdup
 * Return          : null if argument is null otherwise return value form strdump
 */
char *
strdup_with_nullcheck( const char * str1)
{
  if(str1 == NULL)
    return NULL;
  return strdup(str1);
}


/* Helper function to trim white space around the core dump folder location */
char *
trim_white_space(char *string)
{
   char *endptr;
   char *beginptr = string;

   if(string == NULL)
   {
      return NULL;
   }
   /* Remove the white spaces at the beginning */
   while (isspace( (unsigned char)(*beginptr)))
   {
      beginptr++;
   }
   /* if the string contains only whitespace character */
   if(*beginptr == 0)
   {
      return beginptr;
   }

   /* Move the terminating null character next to the last non
      whitespace character */
   endptr = beginptr + strlen(beginptr) - 1;
   while(endptr > beginptr && (isspace( (unsigned char)(*endptr))) )
   {
      endptr--;
   }

   /* endptr points to the last valid entry, now the next entry should be
      terminating null character */
   *(endptr+1) = 0;
   return beginptr;
}

/* Helper function to compile the regex pattern */
int
compile_corefile_pattern (regex_t * regexst, const char * pattern)
{
    int status = regcomp (regexst, pattern, REG_EXTENDED|REG_NEWLINE);
    return status;
}

/* Function       : sev_level
 * Responsibility : To convert severity strings to values
 * return         : -1 if failed, otherwise severity value
 */
int
sev_level(char *arg)
{
    const char *sev[] = {"emer","alert","crit","err","warn","notice","info","debug"};
    int i = 0, found = 0;
    for(i = 0; i < MAX_SEVS; i++)
    {
        if(!strcmp_with_nullcheck(arg, sev[i])) {
            found = 1;
            break;
        }
    }
    if(found) {
        return i;
    }
    return -1;
}

/* Function       : get_values
 * Responsibility : read only values from keys
 * return         : return value
 */

const char*
get_value(const char *str)
{
   if(!str) {
      return NULL;
   }
   while(*str!='\0')
   {
      /*found the split*/
      if(*str == '=')  {
          if(*(str+1))  {
             /*value is present*/
               return str+1;
           }
          return NULL;
      }
      str++;
   }
return NULL;
}

/* Function  : get_yaml_tokens
 * Responsibility : to read yaml file tokens.
 */
char*
get_yaml_tokens(yaml_parser_t *parser,  yaml_event_t **tok, FILE *fh)
{
    char *key;
    yaml_event_t *token = *tok;
    if(fh == NULL) {
        return NULL;
    }
    if(!yaml_parser_parse(parser, token)) {
        return NULL;
    }

    if(token == NULL) {
        return NULL;
    }
    while(token->type!= YAML_STREAM_END_EVENT)
    {
        switch(token->type)
        {
            case YAML_SCALAR_EVENT:
                key = (char*)token->data.scalar.value;
                return key;

            default: break;
        };
        if(token->type != YAML_STREAM_END_EVENT) {
            yaml_event_delete(token);
        }
        if(!yaml_parser_parse(parser, token)) {
            return NULL;
        }
    }
    return NULL;
}

/* Function  : strupr
 * Responsibility : to convert from lower case to upper.
 * return : NULL on failure, otherwise string
 */
char*
strnupr(char *str, int size)
{
    int count = 0;
    unsigned char *p = (unsigned char *)str;
    if(str == NULL) {
        return NULL;
    }

    while (*p) {
        *p = toupper(*p);
        p++;
        count++;
        if(count == size) {
            break;
        }
    }

    return str;
}

/*
 * Function           : strlwr
 * Responsibility     : To convert string from upper to lower case
 */
char*
strnlwr(char *str, int size)
{
    int count = 0;
    unsigned char *p = (unsigned char *)str;
    if(str == NULL) {
        return NULL;
    }
    while (*p) {
        *p = tolower(*p);
        p++;
        count++;
        if(count == size) {
            break;
        }
    }
    return str;
}



/*
 * Function       : validate_cli_args
 * Responsibility : validates given cli argument with regular expression.
 * Parameters
 *                : arg - argument passed in cli
 *                : regex - regular expression to validate user input
 *
 * Returns        : 0 on success
 */

int
validate_cli_args(const char * arg , const char * regex)
{
    regex_t r;
    int rc = 0;
    const int n_matches = 10;
    regmatch_t m[n_matches];

    if (!( arg && regex ) )
        return 1;

    rc = regcomp(&r, regex , REG_EXTENDED|REG_NEWLINE);
    if ( rc )  {
        regfree (&r);
        return rc;
    }

    rc = regexec (&r,arg,n_matches, m, 0);
    regfree (&r);
    return rc;
}

/*
 * Function       : read_pid_file
 * Responsibility : read pid file
 *
 * Parameters
 *                : pidfile
 *
 * Returns        : Negative integer value on failure
 *                  Positive integer value on success
 *
 * Note : read_pidfile() API is does same thing but it opens a file in "r+"
 *        mode. read_pidfile() API will success only if user has "rw"permission.
 *        If user has "r" permission then read_pidfile() API fails.
 */

static int
read_pid_file (char *pidfile)
{
    FILE *fp = NULL;
    int pid = 0;
    int rc = 0;
    char err_buf[MAX_STR_BUFF_LEN] = {0};

    if(pidfile == NULL) {
        VLOG_ERR("Invalid parameter pidfile");
        return -1;
    }

    fp = fopen(pidfile,"r");
    if (fp == NULL) {
        strerror_r (errno,err_buf,sizeof(err_buf));
        STR_SAFE(err_buf);
        VLOG_ERR("Failed to open pidfile:%s , error:%s",pidfile,err_buf);
        return -1;
    }

    rc = fscanf(fp, "%d", &pid);
    fclose(fp);

    /*
     * valid pid range : 1 to 65536
     * digit count range of valid pid : 1 to 5
     */

    if ((( rc >= MIN_PID_LEN ) && ( rc <= MAX_PID_LEN )) &&
            (( pid >= MIN_PID ) && ( pid <= MAX_PID ))) {
        return pid;
    }
    else {
        VLOG_ERR("Pid value is not in range : (%d-%d), pid : %d",
                MIN_PID , MAX_PID , pid);
        return -1;
    }
}

/*
 * Function       : connect_to_daemon
 * Responsibility : populates jsonrpc client structure for a daemon
 * Parameters     : target  - daemon name
 * Returns        : jsonrpc client on success
 *                  NULL on failure
 *
 */

struct jsonrpc*
connect_to_daemon(const char *target) {
    struct jsonrpc *client=NULL;
    char *socket_name=NULL;
    int error=0;
    char * rundir = NULL;
    char *pidfile_name = NULL;
    pid_t pid=-1;

    if (!target) {
        VLOG_ERR("target is null");
        return NULL;
    }

    rundir = (char*) ovs_rundir();
    if (!rundir) {
        VLOG_ERR("rundir is null");
        return NULL;
    }

    socket_name = xasprintf("%s/%s.ctl", rundir, target);
    if (access(socket_name, W_OK) != 0) {
        free(socket_name);
        pidfile_name = xasprintf("%s/%s.pid", rundir, target);
        if (!pidfile_name) {
            VLOG_ERR("pidfile_name is null");
            return NULL;
        }

        pid = read_pid_file(pidfile_name);
        if (pid < 0) {
            VLOG_ERR("cannot read pidfile :%s", pidfile_name);
            free(pidfile_name);
            return NULL;
        }
        free(pidfile_name);
        socket_name = xasprintf("%s/%s.%ld.ctl", rundir , target,
                (long int) pid);
        if (!socket_name) {
            VLOG_ERR("socket_name is null");
            return NULL;
        }
    }

    error = unixctl_client_create(socket_name, &client);
    if (error) {
        VLOG_ERR("cannot connect to %s,error=%d", socket_name,error);
        free(socket_name);
        return NULL;
    }
    free(socket_name);

    return client;
}
