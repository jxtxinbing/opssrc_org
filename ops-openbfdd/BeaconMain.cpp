/**************************************************************
* Copyright (c) 2010-2013, Dynamic Network Services, Inc.
* Jake Montgomery (jmontgomery@dyn.com) & Tom Daly (tom@dyn.com)
* Distributed under the FreeBSD License - see LICENSE
***************************************************************/
#include "common.h"
#include "Beacon.h"
#include "utils.h"
#include <string.h>
#include <list>
#include <unistd.h>

#ifdef ENABLE_OVSDB
#include "bfdOvsdbIf.h"
#endif

using namespace std;

int main(int argc, char *argv[])
{
  bool ret;
  Beacon app;
  bool tee = false;
  bool doFork = true;
  int argIndex;
  list<SockAddr> controlPorts;
  list<IpAddr> listenAddrs;
  const char *valueString;

#ifdef ENABLE_OVSDB
  bfd_ovsdb_init(argc, argv);
#endif

#ifdef BFD_DEBUG
  tee = true;
#endif

  //Parse command line options.
  //Be careful what we do here, since we are pre-fork, and we have not initialized
  //utils, logging, etc.
  for (argIndex = 1; argIndex < argc; argIndex++)
  {
    if (0 == strcmp("--notee", argv[argIndex]))
    {
      tee = false;
    }
    else if (0 == strcmp("--tee", argv[argIndex]))
    {
      tee = true;
    }
    else if (0 == strcmp("--nofork", argv[argIndex]))
    {
      doFork = false;
    }
    else if (0 == strcmp("--version", argv[argIndex]))
    {
      fprintf(stdout, "%s version %s\n", BeaconAppName, SofwareVesrion);
      exit(0);
    }
    else if (CheckArg("--control", argv[argIndex], &valueString))
    {
      SockAddr addrVal;

      if (!valueString || *valueString == '\0')
      {
        fprintf(stderr, "--control must be followed by an '=' and a ip address with a port.\n");
        exit(1);
      }

      if (!addrVal.FromString(valueString))
      {
        fprintf(stderr, "--control address <%s> is not an IPv4 or IPv6 address.\n", valueString);
        exit(1);
      }

      if (!addrVal.HasPort())
      {
        fprintf(stderr, "--control address must have a port specified. The address <%s> does not contain a port.\n", valueString);
        exit(1);
      }

      controlPorts.push_back(addrVal);
    }
    else if (CheckArg("--listen", argv[argIndex], &valueString))
    {
      IpAddr addrVal;

      if (!valueString || *valueString == '\0')
      {
        fprintf(stderr, "--listen must be followed by an '=' and a ip address (may be 0.0.0.0 or ::).\n");
        exit(1);
      }

      if (!addrVal.FromString(valueString))
      {
        fprintf(stderr, "--listen address <%s> is not an IPv4 or IPv6 address.\n", valueString);
        exit(1);
      }

      listenAddrs.push_back(addrVal);
    }
    else
    {
      fprintf(stderr, "Unrecognized %s command line option %s.\n", BeaconAppName, argv[argIndex]);
      exit(1);
    }
  }

  if (doFork)
  {
#ifndef ENABLE_OVSDB
    tee = false;
    if (0 != daemon(1, 0))
    {
      fprintf(stderr, "Failed to daemonize. Exiting.\n");
      exit(1);
    }
#endif
  }

  srand(time(NULL));

  if (!UtilsInit() || !UtilsInitThread())
  {
    fprintf(stderr, "Unable to init thread local storage. Exiting.\n");
    exit(1);
  }

  if (controlPorts.empty())
  {
    SockAddr addr;
    addr.FromString("127.0.0.1", PORTNUM);
    controlPorts.push_back(addr);
    addr.FromString("127.0.0.1", ALT_PORTNUM);
    controlPorts.push_back(addr);
  }


  if (listenAddrs.empty())
  {
    IpAddr addr;
    addr.FromString("0.0.0.0");
    listenAddrs.push_back(addr);
    addr.FromString("::");
    listenAddrs.push_back(addr);
  }

  // Setup logging first
  gLog.SetLogLevel(Log::Detailed);
  gLog.LogToSyslog("bfdd-beacon", tee);
  gLog.Message(Log::App, "Started %d", getpid());

  ret = app.Run(controlPorts, listenAddrs);

  gLog.Message(Log::App, "Shutdown %d", getpid());

  return ret ? 0 : 1;
}
