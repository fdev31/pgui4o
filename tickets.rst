Tickets
=======

:total-count: 14

--------------------------------------------------------------------------------

Get position from printer !
===========================

:bugid: 2
:created: 2019-02-18T01:50:27
:priority: 0

--------------------------------------------------------------------------------

Investigate why fonts are rendered very differently on the raspberry
====================================================================

:bugid: 5
:created: 2019-02-18T22:59:27
:priority: 0

probably a DPI issue

--------------------------------------------------------------------------------

Add some commands
=================

:bugid: 9
:created: 2019-02-23T11:46:51
:priority: 0

- Allow some file operations
   - re-print last
   - list from uploaded
   - get from thingiverse ??

- pid tune ?

--------------------------------------------------------------------------------

Review error handling
=====================

:bugid: 10
:created: 2019-03-10T23:41:42
:priority: 0

Sometimes the feedback circle isn't showing the right color

--------------------------------------------------------------------------------

Allow fast increment while long pressing
========================================

:bugid: 11
:created: 2019-03-10T23:43:06
:priority: 0

Long press increments the same way
it should increment faster

--------------------------------------------------------------------------------

Introduce something nice to get the ui/controller ratio
=======================================================

:bugid: 14
:created: 2019-04-25T00:29:36
:priority: 0
:started: 2019-04-25T00:29:45

Current print speed is a mess
make something to fix this

Some kind of two-ways bridge between UI input & processed values

- should be provided by the UI
   - probably in layout ? Introduce something new, ``transformers``?
- registers layer allowed to transform the data on user input (used by current lambdas ?)
