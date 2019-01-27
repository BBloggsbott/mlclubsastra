drop table if exists members;
create table members (
  regno integer primary key,
  name text not null,
  score integer not null default 0,
  password text not null,
  kaggle text not null
);
drop table if exists tasks;
create table tasks (
    task text not null, 
    ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
drop table if exists submissions;
create table submissions(
  regno integer not null,
  sublink text not null, 
  ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);